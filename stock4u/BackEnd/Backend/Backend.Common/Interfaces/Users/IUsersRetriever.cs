using Backend.Common.Models.Users;
using Backend.Common.Models.InvestingAdvisor;

namespace Backend.Common.Interfaces.Users;

public interface IUsersRetriever
{
    Task<RiskLevel>  GetUserRiskLevel(string UserId);
    Task LoginAsync(LoginUserRequest loginUserRequest);
}
