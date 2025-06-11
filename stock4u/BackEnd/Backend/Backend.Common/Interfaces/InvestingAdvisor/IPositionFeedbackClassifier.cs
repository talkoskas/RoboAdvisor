using Backend.Common.Models.Positions;

namespace Backend.Common.Interfaces.InvestingAdvisor;

public interface IPositionFeedbackClassifier
{
    Task<PositionFeedback> GetPositionFeedbackAsync(UserPositionHistory position);
}