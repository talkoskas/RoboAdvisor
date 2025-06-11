import Typography from '@mui/material/Typography';
import Avatar from '@mui/material/Avatar';
import { useState, useEffect, useContext } from 'react';
import { authContext } from '../Context/auth.context';
import { getUserAchievements } from '../Services/Backend.service';
import { styled } from '@mui/material';
import { Stars } from '@mui/icons-material';

function SidePanel() {

  const [achievements, setAchievements] = useState([]);
  const [auth] = useContext(authContext);
  
  useEffect(() => {
    async function getAchivements() {
        if (!auth || !auth.userId)
        {
            return;
        }
      
        try {
            const achievementsResponse = await getUserAchievements(auth.userId);
            setAchievements(achievementsResponse.data);
        } catch (e) {
            console.log(e);
        }
      
    };
    if (!achievements.length)
    {
      getAchivements();
    }
  }, [auth]);

  return (
    <Container>
      <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', height: '100vh'}}>
        <div style={{paddingTop: '15px', paddingLeft: '6px', paddingRight: '6px'}}>

            <Typography variant="h6" gutterBottom> Achievements </Typography>

            {achievements.map((achivement, index) =>  <Item key={index}>
              <Stars sx={{ width: 35, height: 35, marginRight: '4px', color: '#bdbdbd' }}/>
              <div>
                <Typography variant="h8" gutterBottom> {achivement.achievementType} </Typography>
                <UpdateDate>
                  <Typography sx={{ width: 10, height: 10, marginRight: '10px' }}  variant="h10" gutterBottom>  {(new Date(achivement.achievedTime)).toLocaleDateString()} </Typography>
                </UpdateDate>
              </div>
            </Item>)}
        </div>
      </div>
    </Container>
  );
}

const Container = styled('div')`
  text-align: center;
  border-left: solid 2px #E2DAD6;
  height: 100%;
`

const Item = styled('div')`
  display: flex;
  padding: 10px;
`

const UpdateDate = styled('div')`
  font-size: 11px;
  position: absolute;
`

export default SidePanel;
