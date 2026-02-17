import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  bookSidebar: [
    'index',
    'intro',
    {
      type: 'category',
      label: 'Modules',
      collapsed: false,
      items: [
        'module1-ros2',
        'module2-gazebo-unity',
        'module3-isaac',
        'module4-vla',
      ],
    },
    'capstone',
    'resources',
    'chatbot-guide',
  ],
};

export default sidebars;
