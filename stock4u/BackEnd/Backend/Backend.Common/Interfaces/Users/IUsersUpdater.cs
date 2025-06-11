using Backend.Common.Models.Users;

namespace Backend.Common.Interfaces.Users;

public interface IUsersUpdater
{
    Task RegisterAsync(RegisterUserRequest registerUserRequest);
}
