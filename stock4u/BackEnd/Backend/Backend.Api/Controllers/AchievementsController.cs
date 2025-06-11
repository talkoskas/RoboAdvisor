using Backend.Common.Interfaces.Achievements;
using Backend.Common.Interfaces.InvestingAdvisor;
using Microsoft.AspNetCore.Mvc;

namespace Backend.Api.Controllers;

[ApiController]
[Route("[controller]/[action]")]
public class AchievementsController(
    IAchievementsHandler achievementsHandler,
    ILogger<InvestingAdvisorController> logger) : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetAllAchievementsAsync()
    {
        try
        {
            var userInvestmentStatus = await achievementsHandler.GetAllAchievementsAsync();
            return StatusCode(StatusCodes.Status200OK, userInvestmentStatus);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting all achievements");
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }
    
    [HttpGet]
    public async Task<IActionResult> GetUserAchievementsAsync(string userId)
    {
        try
        {
            var userInvestmentStatus = await achievementsHandler.GetUserAchievementsAsync(userId);
            return StatusCode(StatusCodes.Status200OK, userInvestmentStatus);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting user achievements {userId}", userId);
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }
}