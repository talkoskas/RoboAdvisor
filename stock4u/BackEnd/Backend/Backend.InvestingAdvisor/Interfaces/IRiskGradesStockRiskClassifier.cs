using Backend.Common.Models.InvestingAdvisor;

namespace Backend.InvestingAdvisor.Interfaces;

public interface IRiskGradesStockRiskClassifier
{
    Task<RiskLevel> GetStockRiskGradesRiskLevelAsync(string symbol);
}