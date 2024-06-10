// -*- coding: utf-8 -*-
// A library to display spinorama charts
//
// Copyright (C) 2020-2024 Pierre Aubert pierreaubert(at)yahoo(dot)fr
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

/*eslint no-undef: "error"*/

import { describe, expect, it } from 'vitest';
import { urlChangePage } from './pagination.js';

describe('check pagination', () => {

    it('testing default url', () => {
	const url = 'https://www.spinorama.org'
	const newUrl = urlChangePage(url, 2);
        expect(newUrl).toContain('page=2');
    });

    it('testing preserve parameters', () => {
	const url = 'https://www.spinorama.org/?brand=JBL'
	const newUrl = urlChangePage(url, 2);
        expect(newUrl).toContain('page=2');
        expect(newUrl).toContain('brand=JBL');
    });

});

