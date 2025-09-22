
import { persistence } from './persistence';

export const initializeMockData = async () => {
  if (await persistence.getItem('beauty_bookings')) return;

  const mockBookings = [
    {
      id: 1,
      service: "💅 Маникюр",
      date: "25.12.2024 10:00",
      duration: 90,
      contacts: "📱 +7 (978) 123-45-67",
      timestamp: "2024-12-20T10:00:00Z",
      chat_id: 123456789,
      user_id: 1373071419,
      username: "admin_manicure",
      first_name: "Администратор",
      last_name: "Маникюра",
      status: "confirmed"
    },
    {
      id: 2,
      service: "🧖 Лазерная эпиляция",
      date: "26.12.2024 14:30",
      duration: 30,
      contacts: "📧 client@example.com",
      timestamp: "2024-12-20T11:30:00Z",
      chat_id: 987654321,
      user_id: 1094720117,
      username: "admin_other",
      first_name: "Администратор",
      last_name: "Других услуг",
      status: "pending"
    },
    {
      id: 3,
      service: "👣 Педикюр",
      date: "27.12.2024 16:00",
      duration: 90,
      contacts: "📱 +7 (978) 987-65-43",
      timestamp: "2024-12-20T12:15:00Z",
      chat_id: 555555555,
      user_id: 130208292,
      username: "admin_all",
      first_name: "Главный",
      last_name: "Администратор",
      status: "completed"
    }
  ];

  const adminConfig = {
    ADMIN_MANICURE: "1373071419",
    ADMIN_OTHER: "1094720117",
    ADMIN_ALL: "130208292"
  };

  await persistence.setItem('beauty_bookings', JSON.stringify(mockBookings));
  await persistence.setItem('admin_config', JSON.stringify(adminConfig));
};

export const addTestData = async () => {
  await initializeMockData();
  console.log('Тестовые данные добавлены');
};
