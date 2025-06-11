import './Leaderboard.css';
import * as React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { styled } from '@mui/material/styles';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import { useState, useEffect, useContext } from 'react';
import { authContext } from '../../Context/auth.context';
import { getTopTenUsers, getInvestorStatus } from '../../Services/Backend.service';

const StyledTableCell = styled(TableCell)(({ theme }) => ({
    borderBottom: '1px solid #6482AD',
    color: '#fff'
}));
  
function createData(position, name, achievements, profit) {
    return { position, name, achievements, profit };
}

function Leaderboard() {
    const [rows, setRows] = useState([]);
    const [profit, setProfit] = useState(0);
    const [position, setPosition] = useState(0);
    const [achievements, setAchievements] = useState(0);
    const initialBalance = 1_000_000;

    const [auth,setAuth] = useContext(authContext);

    useEffect(() => {
        async function getRows() {
            try {
                const leaderboardResposne = await getTopTenUsers();
           
                const leaderboard = leaderboardResposne.data;

                const leaderboardRows = leaderboard.map(( {userId, achievementsPoints, totalWorth }, index) => {
                    return createData(index, userId, achievementsPoints, totalWorth);
                });

                setPosition((leaderboardRows.find(data => auth.userId === data.userId)?.index ?? 0) + 1);

    
                setRows(leaderboardRows);
    
                const userInvestmentStatusResponse = await getInvestorStatus(auth.userId);
    
                setProfit((userInvestmentStatusResponse.data.totalWorth - initialBalance).toFixed(2));
                setAchievements(userInvestmentStatusResponse.data.achievementsPoints);
            } catch (e) {
                console.log(e);
            }
        };
    
        if (!rows.length)
        {
            getRows();
        }
      }, []);

    return (
        <div className="App">
            <Typography color="#555" variant="h4" gutterBottom> Leaderboard </Typography>
            <div style={{display: 'flex', justifyContent: 'space-evenly', width: '100%'}}>
                <div className="Card">
                    <Card sx={{ display: 'flex', backgroundColor: '#7FA1C3', color: '#fff', minWidth: '250px', justifyContent: 'center', borderRadius: '8px', minHeight: '120px' }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                            <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" variant="h5">
                                Achievements
                            </Typography>
                            <Typography variant="subtitle1" color="#fff" component="div">
                                {achievements} Points
                            </Typography>
                            </CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                            </Box>
                        </Box>
                    </Card>
                </div>

                <div className="Card">
                    <Card sx={{ display: 'flex', backgroundColor: '#7FA1C3', color: '#fff', minWidth: '250px', justifyContent: 'center', borderRadius: '8px', minHeight: '120px' }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                            <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" variant="h5">
                                Rank
                            </Typography>
                            <Typography variant="subtitle1" color="#fff" component="div">
                                {position}#
                            </Typography>
                            </CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                            </Box>
                        </Box>
                    </Card>
                </div>
              
                <div className="Card">
                    <Card sx={{ display: 'flex', backgroundColor: '#7FA1C3', color: '#fff', minWidth: '250px',  justifyContent: 'center', borderRadius: '8px', minHeight: '120px' }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                            <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" variant="h5">
                                Shares Profit
                            </Typography>
                            <Typography variant="subtitle1" color="#fff" component="div">
                                {profit}$
                            </Typography>
                            </CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                            </Box>
                        </Box>
                    </Card>
                </div>

            </div>
            <div className="LeaderBoard">
                <TableContainer component={Paper} sx={{marginTop: '20px'}}>
                    <Table sx={{backgroundColor: '#7FA1C3'}}>
                        <TableHead>
                            <TableRow>
                                <StyledTableCell sx={{ backgroundColor: '#6482AD' }}>Rank</StyledTableCell>
                                <StyledTableCell sx={{ backgroundColor: '#6482AD' }}>Name</StyledTableCell>
                                <StyledTableCell sx={{ backgroundColor: '#6482AD' }} align="right">Achievements</StyledTableCell>
                                <StyledTableCell sx={{ backgroundColor: '#6482AD' }} align="right">Profit</StyledTableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {rows.map((row) => (
                                <TableRow key={row.position}>
                                <StyledTableCell component="th" scope="row"> {row.position + 1} </StyledTableCell>
                                <StyledTableCell component="th" scope="row"> {row.name} </StyledTableCell>
                                <StyledTableCell align="right">{row.achievements}</StyledTableCell>
                                <StyledTableCell align="right">{row.profit}$</StyledTableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </div>

        </div>
    );
}

export default Leaderboard;
