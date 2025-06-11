using Backend.Common.Interfaces.Users;
using Backend.Common.Models.InvestingAdvisor;
using Backend.Common.Models.Users;

namespace Backend.Bl.Lib;

public class UsersHandler(IUsersUpdater usersUpdater, IUsersRetriever usersRetriever) : IUsersHandler
{
    public async Task<RiskLevel> GetUserRiskLevel(string UserId) 
    {
        return await usersRetriever.GetUserRiskLevel(UserId);
    }

    public async Task RegisterAsync(RegisterUserRequest registerUserRequest)
    {
        await usersUpdater.RegisterAsync(registerUserRequest);
    }

        public async Task LoginAsync(LoginUserRequest loginUserRequest)
    {
        await usersRetriever.LoginAsync(loginUserRequest);
    }
}
