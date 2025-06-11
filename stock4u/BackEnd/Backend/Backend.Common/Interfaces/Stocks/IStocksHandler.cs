using Backend.Common.Models.Stocks;

namespace Backend.Common.Interfaces.Stocks;

public interface IStocksHandler
{
    Task<RealTimeStock> GetRealTimeStockAsync(string symbol);
    
    Task<Dictionary<string, StockDailyData>> GetStockHistoryAsync(string symbol, int daysBack);
}