using Backend.Common.Models.Stocks;
using Backend.InvestingAdvisor.Models;
using Mapster;

namespace Backend.InvestingAdvisor.Lib.StocksRiskClassification;

public static class FinancialOverviewToStockClassificationDataMapper
{
    public static TypeAdapterConfig GetMapping()
    {
        var config = TypeAdapterConfig.GlobalSettings;
        config.ForType<FinancialOverview, StockClassificationData>()
            .Map(dest => dest.Beta, src => src.Beta == "None" || src.Beta == "-" ? null : src.Beta)
            .Map(dest => dest.Roe, src => src.ReturnOnEquityTTM == "None" || src.ReturnOnEquityTTM == "-" ? null : src.ReturnOnEquityTTM)
            .Map(dest => dest.PeRatio, src => src.PERatio == "None" || src.PERatio == "-" ? null : src.PERatio)
            .Map(dest => dest.PbRatio, src => src.PriceToBookRatio == "None" || src.PriceToBookRatio == "-" ? null : src.PriceToBookRatio)
            .Map(dest => dest.DividendYield, src => src.DividendYield == "None" || src.DividendYield == "-" ? null : src.DividendYield);

        return config;
    }
}