namespace Backend.Common.Models.Stocks;

public class StockDailyData
{
    public decimal OpenPrice { get; set; }
    
    public decimal HighPrice { get; set; }
    
    public decimal LowPrice { get; set; }
    
    public decimal ClosePrice { get; set; }
    
    public decimal Volume { get; set; }
}