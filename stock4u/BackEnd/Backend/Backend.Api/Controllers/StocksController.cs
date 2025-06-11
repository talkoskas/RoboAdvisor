using Backend.Common.Interfaces.Stocks;
using Microsoft.AspNetCore.Mvc;

namespace Backend.Api.Controllers;

[ApiController]
[Route("[controller]/[action]")]
public class StocksController(IStocksHandler stocksHandler, ILogger<StocksController> logger) : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetRealTimeStockAsync(string symbol)
    {
        try
        {
            var realTimeStock = await stocksHandler.GetRealTimeStockAsync(symbol);
            return StatusCode(StatusCodes.Status200OK, realTimeStock);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting real time stock {symbol}", symbol);
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }
    
    [HttpGet]
    public async Task<IActionResult> GetStockHistoryAsync(string symbol, int daysBack)
    {
        try
        {
            var stockHistory = await stocksHandler.GetStockHistoryAsync(symbol, daysBack);
            return StatusCode(StatusCodes.Status200OK, stockHistory);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting stock history {symbol} {daysBack} days back", symbol, daysBack);
            return StatusCode(StatusCodes.Status500InternalServerError, exception.Message);
        }
    }
}