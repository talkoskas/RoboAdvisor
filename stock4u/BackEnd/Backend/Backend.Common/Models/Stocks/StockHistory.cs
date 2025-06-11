using System.Text.Json.Serialization;

namespace Backend.Common.Models.Stocks;

public class StockHistory
{
    [JsonPropertyName("Time Series (Daily)")]
    public Dictionary<string, StockDailyDataResponse> DateToStockData { get; set; } = null!;
}