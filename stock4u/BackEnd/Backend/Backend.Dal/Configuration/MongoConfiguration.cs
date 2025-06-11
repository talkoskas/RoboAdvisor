namespace Backend.Dal.Configuration;

public class MongoConfiguration
{
    public string ConnectionString { get; set; } = null!;
    
    public string DbName { get; set; } = null!;
    
    public string UserPositionsCollectionName { get; set; } = null!;
    
    public string UserPositionsHistoryCollectionName { get; set; } = null!;
    
    public string AchievementsCollectionName { get; set; } = null!;
    
    public string UserToAchievementCollectionName { get; set; } = null!;

    public string UsersCollectionName { get; set; } = null!;

    public string RiskLevelComparisonCollectionName { get; set; } = null!;
    
    public string RecommendedStocks { get; set; } = null!;
}
