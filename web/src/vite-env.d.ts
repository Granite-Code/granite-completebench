/// <reference types="vite/client" />

declare module '*.md' {
    import React from 'react';
    const ReactComponent: React.FC;
    export { ReactComponent };
}
