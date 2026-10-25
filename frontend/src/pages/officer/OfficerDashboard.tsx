import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { RegionalOfficerWorkspace } from './RegionalOfficerWorkspace';
import { BureauOfficerWorkspace } from './BureauOfficerWorkspace';
import { CommitteeMemberWorkspace } from './CommitteeMemberWorkspace';
import { EVCCoordinatorWorkspace } from './EVCCoordinatorWorkspace';
import { CompetentAuthorityWorkspace } from './CompetentAuthorityWorkspace';
import { SystemAdminWorkspace } from './SystemAdminWorkspace';

export const OfficerDashboard: React.FC = () => {
  const { activeRole } = useAuth();

  switch (activeRole) {
    case 'BUREAU_OFFICER':
      return <BureauOfficerWorkspace />;
    case 'COMMITTEE_MEMBER':
      return <CommitteeMemberWorkspace />;
    case 'EVC_COORDINATOR':
      return <EVCCoordinatorWorkspace />;
    case 'COMPETENT_AUTHORITY':
      return <CompetentAuthorityWorkspace />;
    case 'SYSTEM_ADMIN':
      return <SystemAdminWorkspace />;
    case 'REGIONAL_OFFICER':
    default:
      return <RegionalOfficerWorkspace />;
  }
};

export default OfficerDashboard;
