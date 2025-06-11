using Backend.Common.Models.Stocks;

namespace Backend.Common.Interfaces.Stocks;

public interface IStockPriceRetriever
{
    Task<RealTimeStock> GetRealTimeStockAsync(string symbol);

    Task<Dictionary<string, StockDailyData>> GetStockHistoryAsync(string symbol, int daysBack = 100);

    Task<FinancialOverview?> GetStockFinancialOverviewAsync(string symbol);
    
    Task<decimal> GetStockStandardDeviationAsync(string symbol);
}