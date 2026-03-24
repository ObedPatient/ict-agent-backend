import json
import base64
import urllib.request
import urllib.error
import re
import logging
from datetime import datetime, timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import ChartAnalysis
from .forms import ChartAnalysisForm
from .ict_prompt import ICT_SYSTEM_PROMPT
from .session_detector import get_session_info

logger = logging.getLogger(__name__)

def index(request):
    """API endpoint to get app info"""
    session = get_session_info()
    steps = [
        {'title': 'Auto-detect pair & timeframe', 'desc': 'Reads symbol and TF directly from your chart image'},
        {'title': 'Determine current session', 'desc': 'Detects NY time at upload and identifies active killzone'},
        {'title': 'Read market structure', 'desc': 'Identifies BOS, CHoCH, HH/HL/LH/LL across the chart'},
        {'title': 'Locate liquidity pools', 'desc': 'Finds BSL, SSL, EQH/EQL and swept levels'},
        {'title': 'Identify POIs', 'desc': 'Marks OBs, FVGs, breakers and OTE zones (62-79% fib)'},
        {'title': 'Confluence check & decision', 'desc': 'Requires 3+ ICT confluences — outputs TRADE, WAIT, or NO TRADE'},
    ]
    concepts = [
        {'name': 'Order Blocks (OB)', 'color': '#58a6ff'},
        {'name': 'Fair Value Gaps (FVG)', 'color': '#00d4aa'},
        {'name': 'BOS / CHoCH', 'color': '#ffa502'},
        {'name': 'Liquidity Sweeps', 'color': '#ff4757'},
        {'name': 'PDH / PDL', 'color': '#a371f7'},
        {'name': 'OTE (62-79% fib)', 'color': '#f78166'},
        {'name': 'Power of 3 (AMD)', 'color': '#58a6ff'},
        {'name': 'Premium / Discount', 'color': '#00d4aa'},
        {'name': 'Killzones', 'color': '#ffa502'},
        {'name': 'Market Maker Models', 'color': '#a371f7'},
    ]
    
    # Return JSON for API
    return JsonResponse({
        'session': session,
        'steps': steps,
        'concepts': concepts,
    })

def history(request):
    """API endpoint to get analysis history"""
    analyses = ChartAnalysis.objects.all()
    trade_count = analyses.filter(signal='TRADE').count()
    no_trade_count = analyses.filter(signal='NO_TRADE').count()
    
    # Return JSON for API
    return JsonResponse({
        'analyses': [
            {
                'id': a.id,
                'pair': a.pair,
                'timeframe': a.timeframe,
                'signal': a.signal,
                'bias': a.bias,
                'created_at': a.created_at.isoformat(),
                'chart_image_url': a.chart_image.url if a.chart_image else None,
                'session': a.session,
            }
            for a in analyses
        ],
        'trade_count': trade_count,
        'no_trade_count': no_trade_count,
    })

def analysis_detail(request, pk):
    """API endpoint to get analysis details"""
    analysis = get_object_or_404(ChartAnalysis, pk=pk)
    
    return JsonResponse({
        'id': analysis.id,
        'pair': analysis.pair,
        'timeframe': analysis.timeframe,
        'signal': analysis.signal,
        'bias': analysis.bias,
        'market_structure': analysis.market_structure,
        'key_levels': analysis.key_levels,
        'entry_price': analysis.entry_price,
        'stoploss': analysis.stoploss,
        'tp1': analysis.tp1,
        'tp2': analysis.tp2,
        'rr_ratio': analysis.rr_ratio,
        'full_analysis': analysis.full_analysis,
        'wait_condition': analysis.wait_condition,
        'no_trade_reason': analysis.no_trade_reason,
        'created_at': analysis.created_at.isoformat(),
        'chart_image_url': analysis.chart_image.url if analysis.chart_image else None,
        'risk_percent': analysis.risk_percent,
        'notes': analysis.notes,
        'session': analysis.session,
        'ny_time': analysis.ny_time,
    })

def call_openrouter(api_key, image_data, media_type, user_context):
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = json.dumps({
        "model": "openai/gpt-5.2",
        "max_tokens": 2000,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": ICT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_data}"}
                    },
                    {"type": "text", "text": user_context}
                ]
            }
        ]
    }).encode('utf-8')

    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "ICT Agent"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        data = json.loads(response.read().decode('utf-8'))

    if "error" in data:
        raise ValueError(data["error"].get("message", str(data["error"])))

    return data["choices"][0]["message"]["content"]

def parse_ai_response(response_text):
    print(f"\n===== RAW AI RESPONSE =====\n{response_text[:3000]}\n===========================\n")

    clean = response_text.strip()
    clean = re.sub(r'^```[a-zA-Z]*\s*', '', clean)
    clean = re.sub(r'\s*```\s*$', '', clean)
    clean = clean.strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{[\s\S]*\}', clean)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {
        "detected_pair": "",
        "detected_timeframe": "",
        "signal": "WAIT",
        "bias": "NEUTRAL",
        "market_structure": "See full analysis below.",
        "key_levels": "",
        "entry_price": "",
        "stoploss": "",
        "tp1": "",
        "tp2": "",
        "rr_ratio": "",
        "full_analysis": response_text,
        "wait_condition": "Review the full narrative analysis below — the AI responded with text instead of structured JSON.",
        "no_trade_reason": ""
    }

@csrf_exempt
@require_POST
def analyze(request):
    """API endpoint for chart analysis"""
    form = ChartAnalysisForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid form data', 'details': form.errors}, status=400)

    analysis = form.save()

    # Capture session at exact moment of upload
    utc_now = datetime.now(timezone.utc)
    session_info = get_session_info(utc_now)
    analysis.session = session_info['session_name']
    analysis.ny_time = session_info['ny_time_str']
    analysis.save()

    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        analysis.delete()
        return JsonResponse({
            'error': 'OPENROUTER_API_KEY not configured. Get a free key at https://openrouter.ai/keys'
        }, status=500)

    try:
        with analysis.chart_image.open('rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        ext = analysis.chart_image.name.split('.')[-1].lower()
        media_type_map = {
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png', 'gif': 'image/gif', 'webp': 'image/webp'
        }
        media_type = media_type_map.get(ext, 'image/jpeg')

        user_context = f"""
The chart image has been uploaded at:
- UTC time: {utc_now.strftime('%Y-%m-%d %H:%M UTC')}
- New York time: {session_info['ny_time_str']}
- Active session: {session_info['session_name']}
- Session context: {session_info['session_description']}
- In a killzone: {'YES — HIGH PROBABILITY WINDOW' if session_info['is_killzone'] else 'No'}
- Avoid trading: {'YES — {}'.format(session_info['session_name']) if session_info['avoid_trading'] else 'No'}

Risk per trade: {analysis.risk_percent}%
Trader notes: {analysis.notes if analysis.notes else 'None provided'}

READ the chart image carefully:
1. Identify the trading instrument/pair from the chart header or symbol watermark
2. Identify the timeframe from the chart label or candle structure
3. Perform complete ICT/SMC analysis using the session context above

IMPORTANT: Respond with ONLY a valid JSON object. No preamble, no explanation, no markdown.
Start your response with {{ and end with }}
"""

        response_text = call_openrouter(api_key, image_data, media_type, user_context)
        result = parse_ai_response(response_text)

        # Save auto-detected values from AI
        analysis.pair = result.get('detected_pair', '')
        analysis.timeframe = result.get('detected_timeframe', '')
        analysis.signal = result.get('signal', 'NO_TRADE')
        analysis.bias = result.get('bias', 'NEUTRAL')
        analysis.market_structure = result.get('market_structure', '')
        analysis.key_levels = result.get('key_levels', '')
        analysis.entry_price = result.get('entry_price', '')
        analysis.stoploss = result.get('stoploss', '')
        analysis.tp1 = result.get('tp1', '')
        analysis.tp2 = result.get('tp2', '')
        analysis.rr_ratio = result.get('rr_ratio', '')
        analysis.full_analysis = result.get('full_analysis', '')
        analysis.wait_condition = result.get('wait_condition', '')
        analysis.no_trade_reason = result.get('no_trade_reason', '')
        analysis.save()

        return JsonResponse({'success': True, 'analysis_id': str(analysis.pk)})

    except urllib.error.HTTPError as e:
        analysis.delete()
        try:
            body = e.read().decode('utf-8')
            err = json.loads(body)
            msg = err.get('error', {}).get('message', body)
        except Exception:
            msg = str(e)
        return JsonResponse({'error': f'OpenRouter API error: {msg}'}, status=500)

    except Exception as e:
        analysis.delete()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def delete_analysis(request, pk):
    if request.method == 'POST':
        analysis = get_object_or_404(ChartAnalysis, pk=pk)
        if analysis.chart_image:
            analysis.chart_image.delete()
        analysis.delete()
    return JsonResponse({'success': True})