import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://cgiar-climate-data-hub.github.io',
  base: '/skills',
  integrations: [
    starlight({
      title: 'CDH Skills',
      description: 'AI-powered climate data workflows for agriculture and climate research.',
      logo: {
        src: './src/assets/cgiar-climate-action-logo.png',
        alt: 'CGIAR Climate Action',
        replacesTitle: false,
      },
      customCss: ['./src/styles/custom.css'],
      components: {
        Hero: './src/components/overrides/Hero.astro',
        Header: './src/components/overrides/Header.astro',
        Footer: './src/components/overrides/Footer.astro',
      },
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/CGIAR-Climate-Data-Hub/skills' },
      ],
      editLink: {
        baseUrl: 'https://github.com/CGIAR-Climate-Data-Hub/skills/edit/main/docs-site/src/content/docs/',
      },
      sidebar: [
        {
          label: 'Overview',
          items: [
            { label: 'Getting started', slug: 'getting-started' },
            { label: 'Contributing a skill', slug: 'contributing' },
          ],
        },
        {
          label: 'Skills',
          items: [
            {
              label: 'End-to-end pipelines',
              items: [
                { label: 'GCF Pipeline', slug: 'skills/gcf-pipeline' },
              ],
            },
            {
              label: 'Data acquisition',
              items: [
                { label: 'Climate Data Download', slug: 'skills/climate-data-download' },
                { label: 'Soil Data Download', slug: 'skills/soil-data-download' },
              ],
            },
            {
              label: 'Spatial processing',
              items: [
                { label: 'Geospatial Cube Processor', slug: 'skills/geospatial-cube-processor' },
              ],
            },
            {
              label: 'Modeling & simulation',
              items: [
                { label: 'Spatial Crop Modeler', slug: 'skills/spatial-crop-modeler' },
              ],
            },
            {
              label: 'Visualization & reporting',
              items: [
                { label: 'Notebook Plots', slug: 'skills/notebook-plots' },
                { label: 'Climate Dashboard', slug: 'skills/climate-dashboard' },
              ],
            },
            {
              label: 'Metadata & cataloging',
              items: [
                { label: 'CDH Metadata', slug: 'skills/cdh-metadata' },
              ],
            },
          ],
        },
        {
          label: 'Setup',
          items: [
            { label: 'Claude Code', slug: 'usage/claude-code' },
            { label: 'Antigravity', slug: 'usage/antigravity' },
            { label: 'OpenAI Codex', slug: 'usage/codex' },
          ],
        },
      ],
    }),
  ],
});
