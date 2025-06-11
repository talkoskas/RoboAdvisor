using Backend.Common.Interfaces.InvestingAdvisor;
using Backend.Common.Models.InvestingAdvisor;
using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using Microsoft.Extensions.Logging;
using MongoDB.Driver;

namespace Backend.Dal.Lib;

public class RiskLevelRetriever(
    IMongoHandler mongoHandler,
    MongoConfiguration mongoConfiguration,
    ILogger<RiskLevelRetriever> logger) : IRiskLevelRetriever
{
    private readonly IMongoCollection<RiskLevelComparison> _riskLevelComparisonCollection =
        mongoHandler.GetCollection<RiskLevelComparison>(mongoConfiguration.RiskLevelComparisonCollectionName);

    public async Task<List<RiskLevelComparison>> GetAllRiskLevelComparisonsAsync()
    {
        List<RiskLevelComparison> riskLevelComparisons;
        try
        {
            riskLevelComparisons = await _riskLevelComparisonCollection.AsQueryable().ToListAsync();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting risk level comparisons");
            throw;
        }

        return riskLevelComparisons;
    }
}