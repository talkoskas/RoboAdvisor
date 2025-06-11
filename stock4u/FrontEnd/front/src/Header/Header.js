import './Header.css';
import Button from '@mui/material/Button';
import { useContext } from 'react';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { authContext } from '../Context/auth.context';


function Header() {
  const [auth, setAuth] = useContext(authContext);

  const signOut = () => {
    localStorage.removeItem("Stock4UCredentials");
    window.location.reload();
    setAuth({});
  }

  return (
    <div>
      <header className="Header-Styles">
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static" enableColorOnDark color="transparent" sx={{ boxShadow: 'none' }}>
            <Toolbar>
              <Typography variant="h6" noWrap component="div" sx={{ display: { xs: 'none', sm: 'block' } }} > Stock4U
                {(auth && auth.userId) ? `      Hello ${auth.userId}!` : ''}
              </Typography>

              <Box sx={{ flexGrow: 1 }} />
              <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
                {(auth && auth.userId) ? <Button onClick={signOut}> Sign Out </Button> : ''}
              </Box>
            </Toolbar>
          </AppBar>
        </Box>
      </header>
    </div>
  );
}

export default Header;
