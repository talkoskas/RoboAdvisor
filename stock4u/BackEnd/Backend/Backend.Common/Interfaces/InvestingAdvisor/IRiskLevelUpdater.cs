using Backend.Common.Models.InvestingAdvisor;

namespace Backend.Common.Interfaces.InvestingAdvisor;

public interface IRiskLevelUpdater
{
    Task InsertRiskLevelComparisonAsync(string symbol, RiskLevel stock4ULevel, RiskLevel riskGradesLevel);
}