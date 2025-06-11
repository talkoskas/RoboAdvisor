using System.Text.Json.Serialization;

namespace Backend.Common.Models.Stocks;

public class RealTimeStock
{
    [JsonPropertyName("c")]
    public decimal CurrentPrice { get; set; }

    [JsonPropertyName("d")]
    public decimal Change { get; set; }

    [JsonPropertyName("dp")]
    public decimal ChangePercent { get; set; }

    [JsonPropertyName("h")]
    public decimal DayHighPrice { get; set; }

    [JsonPropertyName("l")]
    public decimal DayLowPrice { get; set; }
    
    [JsonPropertyName("o")]
    public decimal DayOpenPrice { get; set; }

    [JsonPropertyName("pc")]
    public decimal PreviousClosePrice { get; set; }
}