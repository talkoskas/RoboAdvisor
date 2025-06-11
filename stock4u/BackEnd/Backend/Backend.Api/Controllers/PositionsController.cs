using Backend.Common.Interfaces.Positions;
using Backend.Common.Models.Positions;
using Microsoft.AspNetCore.Mvc;

namespace Backend.Api.Controllers;

[ApiController]
[Route("[controller]/[action]")]
public class PositionsController(IPositionsHandler positionsHandler, ILogger<PositionsController> logger)
    : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetUserInvestmentStatusAsync(string userId)
    {
        try
        {
            var userInvestmentStatus = await positionsHandler.GetUserInvestmentStatusAsync(userId);
            return StatusCode(StatusCodes.Status200OK, userInvestmentStatus);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting user investment status {userId}", userId);
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }

    [HttpGet]
    public async Task<IActionResult> GetTopTenUsersAsync()
    {
        try
        {
            var userInvestmentStatus = await positionsHandler.GetTopTenUsersAsync();
            return StatusCode(StatusCodes.Status200OK, userInvestmentStatus);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting top ten users");
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }

    [HttpGet]
    public async Task<IActionResult> GetUserPositionsHistoryAsync(string userId)
    {
        try
        {
            var userInvestmentStatus = await positionsHandler.GetUserPositionsHistoryAsync(userId);
            return StatusCode(StatusCodes.Status200OK, userInvestmentStatus);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting user positions history {userId}", userId);
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }

    // todo: add stop limit to enter and close position
    [HttpPost]
    public async Task<IActionResult> EnterPositionAsync(EnterPositionRequest enterPositionRequest)
    {
        try
        {
            await positionsHandler.EnterPositionAsync(enterPositionRequest);
            return StatusCode(StatusCodes.Status200OK);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error entering position {@position}", enterPositionRequest);
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }

    [HttpPut]
    public async Task<IActionResult> EditStopLimitAsync(EditStopLimitRequest editStopLimitRequest)
    {
        try
        {
            await positionsHandler.EditStopLimitAsync(editStopLimitRequest);
            return StatusCode(StatusCodes.Status200OK);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error editing stop limit {@position}", editStopLimitRequest);
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }

    [HttpPost]
    public async Task<IActionResult> ClosePositionAsync(ClosePositionRequest closePositionRequest)
    {
        try
        {
            await positionsHandler.ClosePositionAsync(closePositionRequest);
            return StatusCode(StatusCodes.Status200OK);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error closing position {@position}", closePositionRequest);
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }
}