
import { useState, useEffect } from 'react';
import { persistence } from '../../../utils/persistence';

interface AdminConfig {
  ADMIN_MANICURE: string;
  ADMIN_OTHER: string;
  ADMIN_ALL: string;
}

export const useAdminAuth = () => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminId, setAdminId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAdminStatus();
  }, []);

  const checkAdminStatus = async () => {
    try {
      const currentUserId = localStorage.getItem('current_user_id');
      if (!currentUserId) {
        setIsAdmin(false);
        setLoading(false);
        return;
      }

      const adminConfig = await persistence.getItem('admin_config');
      if (adminConfig) {
        const config: AdminConfig = JSON.parse(adminConfig);
        const adminIds = [
          parseInt(config.ADMIN_MANICURE),
          parseInt(config.ADMIN_OTHER),
          parseInt(config.ADMIN_ALL)
        ];

        const userId = parseInt(currentUserId);
        if (adminIds.includes(userId)) {
          setIsAdmin(true);
          setAdminId(userId);
        }
      }
    } catch (error) {
      console.error('Ошибка проверки прав администратора:', error);
    } finally {
      setLoading(false);
    }
  };

  return { isAdmin, adminId, loading };
};
