import IconButton from '@mui/material/IconButton';
import SignalCellularAltRoundedIcon from '@mui/icons-material/SignalCellularAltRounded';
import PaidOutlinedIcon from '@mui/icons-material/PaidOutlined';
import AssignmentOutlinedIcon from '@mui/icons-material/AssignmentOutlined';
import Avatar from '@mui/material/Avatar';
import { Link } from 'react-router-dom';
import { styled } from '@mui/material';


function Menu() {
  return (
    <Container>
      <Header>

          <Button>
            <Avatar sx={{cursor: 'pointer'}} title="Profile" component={Link} to="/profile"/>
          </Button>

          <Button>
            <IconButton component={Link} to="/statistics"> 
                <SignalCellularAltRoundedIcon fontSize='large'/> 
            </IconButton>
            Statistics
          </Button>

          <Button>
            <IconButton component={Link} to="/investments"> 
                <PaidOutlinedIcon fontSize='large'/> 
            </IconButton>
            Investments
          </Button>

          <Button>
            <IconButton component={Link} to="/leaderboard"> 
                <AssignmentOutlinedIcon fontSize='large'/> 
            </IconButton>
            Leaderboard
          </Button>
      </Header>
    </Container>
  );
}

const Container = styled('div')`
  text-align: center;
  border-right: solid 2px #E2DAD6;
  height: 100%;
`

const Header = styled('header')`
  background-color: #F5EDED;
  flex-direction: column;
  font-size: 15px;
  color: #555;
  margin-left: auto; 
  margin-right: 0;
`

const Button = styled('div')`
  padding: 50px;
  flex-direction: column;
  display: flex;
  align-items: center;
`

export default Menu;
