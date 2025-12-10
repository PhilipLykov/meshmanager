import { describe, it, expect } from 'vitest'
import { getRoleName, MESHTASTIC_ROLES } from './meshtastic'

describe('meshtastic utilities', () => {
  describe('MESHTASTIC_ROLES', () => {
    it('should have all 13 role mappings', () => {
      expect(Object.keys(MESHTASTIC_ROLES)).toHaveLength(13)
    })

    it('should have correct role names for known codes', () => {
      expect(MESHTASTIC_ROLES['0']).toBe('Client')
      expect(MESHTASTIC_ROLES['1']).toBe('Client Mute')
      expect(MESHTASTIC_ROLES['2']).toBe('Router')
      expect(MESHTASTIC_ROLES['3']).toBe('Router Client')
      expect(MESHTASTIC_ROLES['4']).toBe('Repeater')
      expect(MESHTASTIC_ROLES['5']).toBe('Tracker')
      expect(MESHTASTIC_ROLES['6']).toBe('Sensor')
      expect(MESHTASTIC_ROLES['7']).toBe('TAK')
      expect(MESHTASTIC_ROLES['8']).toBe('Client Hidden')
      expect(MESHTASTIC_ROLES['9']).toBe('Lost and Found')
      expect(MESHTASTIC_ROLES['10']).toBe('TAK Tracker')
      expect(MESHTASTIC_ROLES['11']).toBe('Router Late')
      expect(MESHTASTIC_ROLES['12']).toBe('Client Base')
    })
  })

  describe('getRoleName', () => {
    it('should return the correct role name for valid codes', () => {
      expect(getRoleName('0')).toBe('Client')
      expect(getRoleName('2')).toBe('Router')
      expect(getRoleName('5')).toBe('Tracker')
      expect(getRoleName('12')).toBe('Client Base')
    })

    it('should return a fallback string for unknown role codes', () => {
      expect(getRoleName('99')).toBe('Role 99')
      expect(getRoleName('unknown')).toBe('Role unknown')
      expect(getRoleName('-1')).toBe('Role -1')
    })

    it('should handle empty string', () => {
      expect(getRoleName('')).toBe('Role ')
    })
  })
})
