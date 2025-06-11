using System.Text.Json.Serialization;

namespace Backend.Common.Models.Stocks;

public class StockDailyDataResponse
{
    [JsonPropertyName("1. open")]
    public string OpenPrice { get; set; }
    
    [JsonPropertyName("2. high")]
    public string HighPrice { get; set; }
    
    [JsonPropertyName("3. low")]
    public string LowPrice { get; set; }
    
    [JsonPropertyName("4. close")]
    public string ClosePrice { get; set; }
    
    [JsonPropertyName("5. volume")]
    public string Volume { get; set; }
}