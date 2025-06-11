namespace Backend.Common.Models.Stocks;

public class FinancialOverview
{
    public string Symbol { get; set; } = null!;
    
    public string AssetType { get; set; } = null!;
    
    public string Name { get; set; } = null!;
    
    public string Description { get; set; } = null!;
    
    public string CIK { get; set; } = null!;
    
    public string Exchange { get; set; } = null!;
    
    public string Currency { get; set; } = null!;
    
    public string Country { get; set; } = null!;
    
    public string Sector { get; set; } = null!;
    
    public string Industry { get; set; } = null!;
    
    public string Address { get; set; } = null!;
    
    public string FiscalYearEnd { get; set; } = null!;
    
    public string LatestQuarter { get; set; } = null!;
    
    public string MarketCapitalization { get; set; }
    
    public string EBITDA { get; set; }
    
    public string PERatio { get; set; }
    
    public string PEGRatio { get; set; }
    
    public string BookValue { get; set; }
    
    public string DividendPerShare { get; set; }
    
    public string DividendYield { get; set; }
    
    public string EPS { get; set; }
    
    public string RevenuePerShareTTM { get; set; }
    
    public string ProfitMargin { get; set; }
    
    public string OperatingMargstringTM { get; set; }
    
    public string ReturnOnAssetsTTM { get; set; }
    
    public string ReturnOnEquityTTM { get; set; }
    
    public string RevenueTTM { get; set; }
    
    public string GrossProfitTTM { get; set; }
    
    public string DilutedEPSTTM { get; set; }
    
    public string QuarterlyEarningsGrowthYOY { get; set; }
    
    public string QuarterlyRevenueGrowthYOY { get; set; }
    
    public string AnalystTargetPrice { get; set; }
    
    public string AnalystRatingStrongBuy { get; set; }
    
    public string AnalystRatingBuy { get; set; }
    
    public string AnalystRatingHold { get; set; }
    
    public string AnalystRatingSell { get; set; }
    
    public string AnalystRatingStrongSell { get; set; }
    
    public string TrailingPE { get; set; }
    
    public string ForwardPE { get; set; }
    
    public string PriceToSalesRatioTTM { get; set; }
    
    public string PriceToBookRatio { get; set; }
    
    public string EVToRevenue { get; set; }
    
    public string EVToEBITDA { get; set; }
    
    public string Beta { get; set; }
    
    public string Week52High { get; set; }
    
    public string Week52Low { get; set; }
    
    public string MovingAverage50Day { get; set; }
    
    public string MovingAverage200Day { get; set; }
    
    public string SharesOutstanding { get; set; }
    
    public string DividendDate { get; set; } = null!;
    
    public string ExDividendDate { get; set; } = null!;
    
}
