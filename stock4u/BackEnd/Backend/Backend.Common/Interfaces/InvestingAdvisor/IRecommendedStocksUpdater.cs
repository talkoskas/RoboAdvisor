using Backend.Common.Models.InvestingAdvisor;

namespace Backend.Common.Interfaces.InvestingAdvisor;

public interface IRecommendedStocksUpdater
{
     Task AddRecommendedStockAsync(string symbol, RiskLevel riskLevel);
}