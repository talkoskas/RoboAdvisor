using Backend.Common.Interfaces.InvestingAdvisor;
using Backend.Common.Models.InvestingAdvisor;

namespace Backend.Bl.Lib;

public class InvestingAdvisorHandler(IStockRiskClassifier stockRiskClassifier, IRiskLevelRetriever riskLevelRetriever)
    : IInvestingAdvisorHandler
{
    public async Task<RiskLevel> ClassifyStockAsync(string symbol)
    {
        return await stockRiskClassifier.GetStockRiskLevelAsync(symbol);
    }

    public async Task<RiskLevelComparisonPercentage> GetRiskLevelClassificationPrecisionAsync()
    {
        var riskLevelComparisons = await riskLevelRetriever.GetAllRiskLevelComparisonsAsync();
        var tooLowClassifications = riskLevelComparisons.Where(riskLevel => riskLevel is
            { Stock4URiskLevel: RiskLevel.Low, RiskGradesRiskLevel: RiskLevel.Medium or RiskLevel.High } or
            { Stock4URiskLevel: RiskLevel.Medium, RiskGradesRiskLevel: RiskLevel.High });
        var tooHighClassifications = riskLevelComparisons.Where(riskLevel => riskLevel is
            { Stock4URiskLevel: RiskLevel.High, RiskGradesRiskLevel: RiskLevel.Medium or RiskLevel.Low } or
            { Stock4URiskLevel: RiskLevel.Medium, RiskGradesRiskLevel: RiskLevel.Low });
        var accurateClassifications =
            riskLevelComparisons.Where(riskLevel => riskLevel.Stock4URiskLevel == riskLevel.RiskGradesRiskLevel);
        var comparisonPercentageModel = new RiskLevelComparisonPercentage
        {
            AccurateClassificationsPercentage = (decimal)accurateClassifications.Count() / riskLevelComparisons.Count * 100,
            TooLowClassificationsPercentage = (decimal)tooLowClassifications.Count() / riskLevelComparisons.Count * 100,
            TooHighClassificationsPercentage = (decimal)tooHighClassifications.Count() / riskLevelComparisons.Count * 100
        };

        return comparisonPercentageModel;
    }
}