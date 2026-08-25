# -*- coding: utf-8 -*-
import re

with open('frontend/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
if 'ReviewForm' not in content:
    content = content.replace(
        "import { CancelModal } from '../components/booking/CancelModal'",
        "import { CancelModal } from '../components/booking/CancelModal'\nimport { ReviewForm } from '../components/ui/ReviewForm'"
    )

# Inject ReviewForm before CancelModal
if '<ReviewForm />' not in content:
    content = content.replace(
        "      <CancelModal",
        "      {/* Reseñas */}\n      <ReviewForm />\n\n      <CancelModal"
    )

with open('frontend/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Injected ReviewForm")
