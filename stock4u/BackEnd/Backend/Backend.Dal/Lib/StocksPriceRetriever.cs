using Backend.Common.Interfaces.Stocks;
using Backend.Common.Models.Stocks;
using Backend.Dal.Configuration;
using Flurl;
using Flurl.Http;
using Mapster;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json.Linq;

namespace Backend.Dal.Lib;

public class StocksPriceRetriever(
    RealTimeStocksApiConfiguration realTimeStocksApiConfiguration,
    HistoryStocksApiConfiguration historyStocksApiConfiguration,
    ILogger<StocksPriceRetriever> logger) : IStockPriceRetriever
{
    // This Api is limited by 60 calls per minute
    private readonly Url _realTimeStocksApiUrl =
        realTimeStocksApiConfiguration.BaseUrl.SetQueryParam("token", realTimeStocksApiConfiguration.ApiKey);

    private readonly Url _historyStocksApiUrl =
        historyStocksApiConfiguration.BaseUrl
            .SetQueryParam("apikey", historyStocksApiConfiguration.ApiKey);

    public async Task<RealTimeStock> GetRealTimeStockAsync(string symbol)
    {
        var fullUrl = _realTimeStocksApiUrl.SetQueryParam("symbol", symbol);

        RealTimeStock response;
        try
        {
            response = await fullUrl.GetJsonAsync<RealTimeStock>();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting real time stock {symbol}", symbol);
            throw;
        }
        
        return response;
    }

    // todo: check last refreshed time
    public async Task<Dictionary<string, StockDailyData>> GetStockHistoryAsync(string symbol, int daysBack)
    {
        var fullUrl = _historyStocksApiUrl
            .SetQueryParam("symbol", symbol)
            .SetQueryParam("function", "TIME_SERIES_DAILY")
            .SetQueryParam("outputsize", "full");
        
        StockHistory response;
        try
        {
            response = await fullUrl.GetJsonAsync<StockHistory>();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting stock history {symbol}", symbol);
            throw;
        }

        if (response.DateToStockData is null)
        {
            logger.LogError("Reached history api limit on request for symbol {symbol}", symbol);
            throw new Exception("Reached history api limit");
        }

        var formattedResponse = response.DateToStockData.Take(daysBack).ToDictionary()
            .Adapt<Dictionary<string, StockDailyData>>();
        return formattedResponse;
    }

    public async Task<FinancialOverview?> GetStockFinancialOverviewAsync(string symbol)
    {
        var fullUrl = _historyStocksApiUrl
            .SetQueryParam("symbol", symbol)
            .SetQueryParam("function", "OVERVIEW");
        
        FinancialOverview response;
        try
        {
            response = await fullUrl.GetJsonAsync<FinancialOverview>();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting stock financial overview {symbol}", symbol);
            throw;
        }

        return response;
    }

    public async Task<decimal> GetStockStandardDeviationAsync(string symbol)
    {
        var fullUrl = _historyStocksApiUrl
            .SetQueryParam("function", "ANALYTICS_FIXED_WINDOW")
            .SetQueryParam("SYMBOLS", symbol)
            .SetQueryParam("RANGE", DateTime.Now.ToString("yyyy-MM-dd"))
            .SetQueryParam("RANGE", DateTime.Now.AddDays(-30).ToString("yyyy-MM-dd"))
            .SetQueryParam("INTERVAL", "DAILY")
            .SetQueryParam("OHLC", "close")
            .SetQueryParam("CALCULATIONS", "STDDEV")
            .SetQueryParam("apikey", historyStocksApiConfiguration.ApiKey);

        object response;
        try
        {
            response = await fullUrl.GetJsonAsync<object>();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting stock standard deviation {symbol}", symbol);
            throw;
        }

        var jobject = JObject.Parse(response.ToString());
        decimal standardDeviation;
        try
        {
            standardDeviation = jobject["payload"]["RETURNS_CALCULATIONS"]["STDDEV"][symbol].Value<decimal>();
        }
        catch (Exception exception)
        {
            return 0;
        }
        return standardDeviation;
    }
}