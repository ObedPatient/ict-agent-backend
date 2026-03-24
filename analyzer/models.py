from django.db import models
import uuid

class ChartAnalysis(models.Model):
    SIGNAL_CHOICES = [
        ('TRADE', 'Trade Setup'), ('WAIT', 'Wait & Watch'), ('NO_TRADE', 'No Trade'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart_image = models.ImageField(upload_to='charts/')

    # Auto-detected from image by AI
    pair = models.CharField(max_length=20, blank=True)
    timeframe = models.CharField(max_length=10, blank=True)

    # Auto-detected from upload time
    session = models.CharField(max_length=40, blank=True)
    ny_time = models.CharField(max_length=20, blank=True)

    # User input — only these two remain
    risk_percent = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    notes = models.TextField(blank=True)

    # Analysis results
    signal = models.CharField(max_length=10, choices=SIGNAL_CHOICES, blank=True)
    bias = models.CharField(max_length=20, blank=True)
    market_structure = models.TextField(blank=True)
    key_levels = models.TextField(blank=True)
    entry_price = models.CharField(max_length=20, blank=True)
    stoploss = models.CharField(max_length=20, blank=True)
    tp1 = models.CharField(max_length=20, blank=True)
    tp2 = models.CharField(max_length=20, blank=True)
    rr_ratio = models.CharField(max_length=10, blank=True)
    full_analysis = models.TextField(blank=True)
    wait_condition = models.TextField(blank=True)
    no_trade_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pair or 'Unknown'} {self.timeframe or ''} - {self.signal} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
