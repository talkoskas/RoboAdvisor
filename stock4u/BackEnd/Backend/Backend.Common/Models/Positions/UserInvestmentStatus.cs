namespace Backend.Common.Models.Positions;

public class UserInvestmentStatus : UserPositions
{
    public decimal TotalWorth { get; set; }
    
    public int AchievementsPoints { get; set; }
    
    public int AchievementsCount { get; set; }
}