using Backend.Common.Interfaces.Achievements;
using Backend.Common.Interfaces.InvestingAdvisor;
using Backend.Common.Models.Achievements;
using Backend.Common.Models.InvestingAdvisor;
using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using Microsoft.Extensions.Logging;
using MongoDB.Driver;
using MongoDB.Driver.Linq;

namespace Backend.Dal.Lib;

public class ReccommendedStocksRetriever(
    IMongoHandler mongoHandler,
    MongoConfiguration mongoConfiguration,
    ILogger<ReccommendedStocksRetriever> logger) : IRecommendedStocksRetriver
{
    private readonly IMongoCollection<RecommendedStocks> Recommended_Stocks =
        mongoHandler.GetCollection<RecommendedStocks>(mongoConfiguration.RecommendedStocks);

    public async Task<List<RecommendedStocks>> GetAllRecommendedStocksAsync()
    {
        List<RecommendedStocks> recommendedStocks;
        try
        {
            recommendedStocks = await Recommended_Stocks.AsQueryable().ToListAsync();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting Recommended Stocks");
            throw;
        }

        return recommendedStocks;
    }

    public async Task<List<RecommendedStocks>> GetRecommendedStocksByRiskAsync(RiskLevel riskLevel)
    {
        List<RecommendedStocks> recommendedStocks;
        try
        {
            recommendedStocks = await Recommended_Stocks.AsQueryable().Where(recommendedStock=> recommendedStock.RiskLevel.Equals(riskLevel)).ToListAsync();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting Recommended Stocks");
            throw;
        }

        return recommendedStocks;
    }
}