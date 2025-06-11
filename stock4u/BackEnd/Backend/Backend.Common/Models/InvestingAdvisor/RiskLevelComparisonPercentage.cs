namespace Backend.Common.Models.InvestingAdvisor;

public class RiskLevelComparisonPercentage
{
    public decimal AccurateClassificationsPercentage { get; set; }
    
    public decimal TooLowClassificationsPercentage { get; set; }
    
    public decimal TooHighClassificationsPercentage { get; set; }
}