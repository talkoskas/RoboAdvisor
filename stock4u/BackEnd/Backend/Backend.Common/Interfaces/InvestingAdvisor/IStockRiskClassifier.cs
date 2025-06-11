using Backend.Common.Models.InvestingAdvisor;

namespace Backend.Common.Interfaces.InvestingAdvisor;

public interface IStockRiskClassifier
{
    Task<RiskLevel> GetStockRiskLevelAsync(string symbol, int daysBack = 30);
}