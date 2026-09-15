import React from 'react';
import { render, screen } from '@testing-library/react';
import { Button } from './Button';
import { describe, it, expect } from 'vitest';
import userEvent from '@testing-library/user-event';

describe('Button Component', () => {
  it('renders correctly', () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    let clicked = false;
    render(<Button onClick={() => clicked = true}>Click Me</Button>);
    
    const button = screen.getByText('Click Me');
    await userEvent.click(button);
    
    expect(clicked).toBe(true);
  });
});
