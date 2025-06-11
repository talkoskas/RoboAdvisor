using Backend.Bl.Configuration;
using Backend.Bl.Interfaces;
using Backend.Bl.Lib;
using Backend.Bl.Lib.Achievements;
using Backend.Common.Interfaces.Achievements;
using Backend.Common.Interfaces.InvestingAdvisor;
using Backend.Common.Interfaces.Positions;
using Backend.Bl.Lib.OrderCommands;
using Backend.Bl.Lib.RecommendedStocks;
using Backend.Common.Interfaces.Stocks;
using Backend.Common.Interfaces.Users;
using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using Backend.Dal.Lib;
using Backend.InvestingAdvisor.Configuration;
using Backend.InvestingAdvisor.Interfaces;
using Backend.InvestingAdvisor.Lib.PositionsFeedback;
using Backend.InvestingAdvisor.Lib.StocksRiskClassification;

namespace Backend.Api;

public static class DependencyInjectionExtensions
{
    public static IServiceCollection AddServices(this IServiceCollection serviceCollection)
    {
        serviceCollection
            .AddSingleton<IPositionsHandler, PositionsHandler>()
            .AddSingleton<IPositionsRetriever, PositionsRetriever>()
            .AddSingleton<IPositionsUpdater, PositionsUpdater>()
            .AddSingleton<IMongoHandler, MongoHandler>()
            .AddSingleton<IRecommendedStocksRetriver, ReccommendedStocksRetriever>()
            .AddSingleton<IRecommendedStocksUpdater, RecommendedStocksUpdater>()
            .AddSingleton<IStocksHandler, StocksHandler>()
            .AddSingleton<IStockPriceRetriever, StocksPriceRetriever>()
            .AddSingleton<IInvestingAdvisorHandler, InvestingAdvisorHandler>()
            .AddSingleton<IStockRiskClassifier, StockRiskClassifier>()
            .AddSingleton<IRiskGradesStockRiskClassifier, RiskGradesStockRiskClassifier>()
            .AddSingleton<IRiskLevelUpdater, RiskLevelUpdater>()
            .AddSingleton<IRiskLevelRetriever, RiskLevelRetriever>()
            .AddSingleton<IPositionFeedbackClassifier, PositionFeedbackClassifier>()
            .AddSingleton<IAchievementsHandler, AchievementsHandler>()
            .AddSingleton<IAchievementsRetriever, AchievementsRetriever>()
            .AddSingleton<IAchievementsUpdater, AchievementsUpdater>()
            .AddSingleton<IUserToAchievementConnector, UserToAchievementConnector>()
            .AddSingleton<IUsersHandler, UsersHandler>()
            .AddSingleton<IUsersUpdater, UsersUpdater>()
            .AddSingleton<IUsersRetriever, UsersRetriever>()
            .AddHostedService<UserToAchievementService>()
            .AddHostedService<RecommendedStocksService>()
            .AddHostedService<ClassifyPositionsService>()
            .AddHostedService<OrderCommandsService>();

        return serviceCollection;
    }

    public static IServiceCollection AddMapping(this IServiceCollection serviceCollection)
    {
        var mapping = FinancialOverviewToStockClassificationDataMapper.GetMapping();
        serviceCollection.AddSingleton(mapping);
        
        return serviceCollection;
    }

    public static IServiceCollection AddConfiguration(this IServiceCollection serviceCollection,
        IConfiguration configuration)
    {
        serviceCollection
            .AddConfiguration<MongoConfiguration>(configuration, "MongoDb")
            .AddConfiguration<RealTimeStocksApiConfiguration>(configuration, "RealTimeStocksApi")
            .AddConfiguration<HistoryStocksApiConfiguration>(configuration, "HistoryStocksApi")
            .AddConfiguration<PositionsFeedbackConfiguration>(configuration, "PositionsFeedback")
            .AddConfiguration<UserToAchievementConfiguration>(configuration, "UserToAchievement")
            .AddConfiguration<OrderCommandsConfiguration>(configuration, "OrderCommands");
        
        return serviceCollection;
    }

    private static IServiceCollection AddConfiguration<T>(this IServiceCollection serviceCollection,
        IConfiguration configuration, string key) where T : class
    {
        var configurationValue = configuration.GetSection(key).Get<T>() ??
                                 throw new ArgumentNullException($"Can't find {key} configuration");
        serviceCollection.AddSingleton(configurationValue);
        return serviceCollection;
    }
}