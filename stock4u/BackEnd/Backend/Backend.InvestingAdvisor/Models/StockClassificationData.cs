namespace Backend.InvestingAdvisor.Models;

public class StockClassificationData
{
    public decimal Beta { get; set; }
    
    public decimal Roe { get; set; }

    public decimal? PeRatio { get; set; }

    public decimal PbRatio { get; set; }
    
    public decimal? DividendYield { get; set; }
}