using Backend.Common.Models.InvestingAdvisor;

namespace Backend.Common.Interfaces.InvestingAdvisor;

public interface IRiskLevelRetriever
{
    Task<List<RiskLevelComparison>> GetAllRiskLevelComparisonsAsync();
}