using Backend.Common.Models.Users;
using Backend.Common.Models.InvestingAdvisor;

namespace Backend.Common.Interfaces.Users;

public interface IUsersHandler
{
    Task<RiskLevel> GetUserRiskLevel(string UserId);
    Task RegisterAsync(RegisterUserRequest registerUserRequest);
    Task LoginAsync(LoginUserRequest loginUserRequest);
}
