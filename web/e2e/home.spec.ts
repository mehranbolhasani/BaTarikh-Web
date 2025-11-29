import { test, expect } from '@playwright/test'

test.describe('Home Page', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/با تاریخ/)
  })

  test('should display filter buttons', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('link', { name: 'همه' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'تصویر' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'ویدئو' })).toBeVisible()
  })

  test('should filter by media type', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: 'تصویر' }).click()
    await expect(page).toHaveURL(/\?type=image/)
  })

  test('should navigate pagination', async ({ page }) => {
    await page.goto('/')
    // Check if pagination exists
    const pagination = page.locator('text=صفحه')
    if (await pagination.isVisible()) {
      // Try to click next page if available
      const nextButton = page.getByRole('link').filter({ hasText: /ArrowLeft/ }).first()
      if (await nextButton.isVisible()) {
        await nextButton.click()
        await expect(page).toHaveURL(/\?page=2/)
      }
    }
  })
})

