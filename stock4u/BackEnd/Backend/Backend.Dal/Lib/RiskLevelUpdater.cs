using Backend.Common.Interfaces.InvestingAdvisor;
using Backend.Common.Models.InvestingAdvisor;
using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using Microsoft.Extensions.Logging;
using MongoDB.Driver;

namespace Backend.Dal.Lib;

public class RiskLevelUpdater(
    IMongoHandler mongoHandler,
    MongoConfiguration mongoConfiguration,
    ILogger<RiskLevelUpdater> logger) : IRiskLevelUpdater
{
    private readonly IMongoCollection<RiskLevelComparison> _riskLevelComparisonCollection =
        mongoHandler.GetCollection<RiskLevelComparison>(mongoConfiguration.RiskLevelComparisonCollectionName);

    public async Task InsertRiskLevelComparisonAsync(string symbol, RiskLevel stock4ULevel, RiskLevel riskGradesLevel)
    {
        var riskLevelComparison = new RiskLevelComparison
        {
            Symbol = symbol,
            ClassificationTime = DateTime.Now,
            Stock4URiskLevel = stock4ULevel,
            RiskGradesRiskLevel = riskGradesLevel
        };
        
        try
        {
            await _riskLevelComparisonCollection.InsertOneAsync(riskLevelComparison);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error inserting risk level comparison {symbol}", symbol);
            throw;
        }
    }
}