using Backend.Common.Interfaces.InvestingAdvisor;
using Backend.Common.Models.InvestingAdvisor;
using Microsoft.AspNetCore.Mvc;

namespace Backend.Api.Controllers;

[ApiController]
[Route("[controller]/[action]")]
public class InvestingAdvisorController(
    IRecommendedStocksRetriver recommendedStocksRetriver,
    IInvestingAdvisorHandler investingAdvisorHandler,
    
    ILogger<InvestingAdvisorController> logger) : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetStockRiskLevelAsync(string symbol)
    {
        try
        {
            var userInvestmentStatus = await investingAdvisorHandler.ClassifyStockAsync(symbol);
            return StatusCode(StatusCodes.Status200OK, userInvestmentStatus);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error classifying stock {symbol}", symbol);
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }
    
    [HttpGet]
    public async Task<IActionResult> GetClassificationPrecisionAsync()
    {
        try
        {
            var riskLevelComparisonPercentage = await investingAdvisorHandler.GetRiskLevelClassificationPrecisionAsync();
            return StatusCode(StatusCodes.Status200OK, riskLevelComparisonPercentage);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting risk level classification precision");
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }
    
    [HttpGet]
    public async Task<IActionResult> GetRecommendedStocksByRiskAsync(RiskLevel riskLevel)
    {
        try
        {
            var recommendedStocks = await recommendedStocksRetriver.GetRecommendedStocksByRiskAsync(riskLevel
            );
            return StatusCode(StatusCodes.Status200OK, recommendedStocks);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error by getting stocks rick level ");
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }
}

