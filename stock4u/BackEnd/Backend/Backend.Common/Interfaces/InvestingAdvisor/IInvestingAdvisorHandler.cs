using Backend.Common.Models.InvestingAdvisor;

namespace Backend.Common.Interfaces.InvestingAdvisor;

public interface IInvestingAdvisorHandler
{
    Task<RiskLevel> ClassifyStockAsync(string symbol);
    
    Task<RiskLevelComparisonPercentage> GetRiskLevelClassificationPrecisionAsync();
}