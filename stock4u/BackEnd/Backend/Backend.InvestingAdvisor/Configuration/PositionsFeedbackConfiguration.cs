using Backend.Common.Models.InvestingAdvisor;

namespace Backend.InvestingAdvisor.Configuration;

public class PositionsFeedbackConfiguration
{
    public double FeedbackCalculationIntervalInMinutes { get; set; } = 60;

    public decimal PeakDropThreshold { get; set; } = 10m;

    public int PostCloseGainWindow { get; set; } = 30;

    public decimal PostCloseGainThreshold { get; set; } = 5m;

    public int PreEntryLossWindow { get; set; } = 10;

    public decimal EntryLossThreshold { get; set; } = 5m;

    public Dictionary<RiskLevel, decimal> PositiveFeedbackThreshold { get; set; } = new()
    {
        { RiskLevel.Low, 0.025m },
        { RiskLevel.Medium, 0.0375m },
        { RiskLevel.High, 0.05m }
    };
}