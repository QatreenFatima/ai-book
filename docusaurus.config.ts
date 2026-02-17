import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Physical AI & Humanoid Robotics',
  tagline: 'Bridging Digital Intelligence and Physical Embodiment',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://ai-book-rouge.vercel.app',
  baseUrl: '/',

  organizationName: 'QatreenFatima',
  projectName: 'ai-book',
  deploymentBranch: 'gh-pages',
  trailingSlash: false,

  onBrokenLinks: 'throw',

  markdown: {
    mermaid: true,
  },

  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Physical AI & Humanoid Robotics',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'bookSidebar',
          position: 'left',
          label: 'Book',
        },
        {
          href: 'https://github.com/QatreenFatima/ai-book',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Book',
          items: [
            {label: 'Introduction', to: '/intro'},
            {label: 'Module 1: ROS 2', to: '/module1-ros2'},
            {label: 'Capstone Project', to: '/capstone'},
          ],
        },
        {
          title: 'Resources',
          items: [
            {label: 'ROS 2 Documentation', href: 'https://docs.ros.org/en/humble/'},
            {label: 'NVIDIA Isaac Sim', href: 'https://developer.nvidia.com/isaac-sim'},
            {label: 'Gazebo Sim', href: 'https://gazebosim.org/'},
          ],
        },
        {
          title: 'Community',
          items: [
            {label: 'ROS Discourse', href: 'https://discourse.ros.org/'},
            {label: 'GitHub', href: 'https://github.com/QatreenFatima/ai-book'},
          ],
        },
      ],
      copyright: `Copyright ${new Date().getFullYear()} Physical AI & Humanoid Robotics Book. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'python', 'yaml', 'markup', 'cpp', 'json'],
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
