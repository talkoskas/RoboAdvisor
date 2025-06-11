using Backend.Common.Models.Stocks;

namespace Backend.InvestingAdvisor.Lib.Utils;

public static class ConversionUtils
{
    public static Dictionary<DateTime, decimal> GetClosePricesDictionary(Dictionary<string, StockDailyData> historyData)
    {
        var closePriceHistory = historyData.ToDictionary(dailyData =>
            DateTime.Parse(dailyData.Key), dailyData => dailyData.Value.ClosePrice);
        return closePriceHistory;
    }

    public static List<StockDatePrice> GetClosePricesList(Dictionary<string, StockDailyData> historyData)
    {
        var closePriceHistory = historyData
            .Select(data => new StockDatePrice
            {
                Date = DateTime.Parse(data.Key),
                ClosePrice = data.Value.ClosePrice
            })
            .OrderBy(data => data.Date)
            .ToList();

        return closePriceHistory;
    }
}