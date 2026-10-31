function run_wsindy_original_q5w(root, limit, input_dir, output_dir)
% Execute the external reference on binary inputs without modifying its files.
if nargin < 1, root = pwd; end
if nargin < 2, limit = inf; end
addpath(fullfile(root, 'outputs', 'reference_wsindy_ode_72d8d6e'));
if nargin < 3, input_dir = fullfile(root, 'outputs', 'sideproject_q5w_wsindy', 'matlab_inputs'); end
if nargin < 4, output_dir = fullfile(root, 'outputs', 'sideproject_q5w_wsindy', 'matlab_outputs'); end
if ~exist(output_dir, 'dir'), mkdir(output_dir); end
manifest = jsondecode(fileread(fullfile(input_dir, 'manifest.json')));
grid = 10.^linspace(-4, 0, 100);
for k = 1:min(numel(manifest.cells), limit)
    cell_info = manifest.cells(k);
    target = fullfile(output_dir, [cell_info.cell_id '.json']);
    if exist(target, 'file')
        saved = jsondecode(fileread(target));
        assert(strcmp(saved.time_sha256,cell_info.time_sha256) && ...
            strcmp(saved.state_sha256,cell_info.state_sha256) && ...
            strcmp(saved.library,cell_info.library), 'Stale completed input');
        continue;
    end
    data = load(fullfile(input_dir, cell_info.input_file));
    [coef,~,~,loss,~,~,~,~,~,~,~,~,~,~,~,tags] = wsindy_ode_fun( ...
        data.xobs,data.tobs,[],[],[],data.requested_tags,{}, ...
        1,1,1e-16,-1,1,1,0,2,0,grid,0,0.8, ...
        0.8,[1;0],[1;0],0,2,ceil(numel(data.tobs)/100));
    permutation = zeros(size(data.requested_tags,1),1);
    for j = 1:numel(permutation)
        found = find(all(tags == data.requested_tags(j,:),2));
        assert(numel(found) == 1, 'Column tags must match uniquely');
        permutation(j) = found;
    end
    assert(size(tags,1) == numel(permutation), 'Unexpected reference columns');
    result = cell_info;
    result.tags_real = real(tags);
    result.tags_imag = imag(tags);
    result.port_to_original_column_index_base1 = permutation;
    equations = repmat(struct('coefficients_original_scale',[], ...
        'support_indices',[], 'lambda_grid_index',[], 'lambda_grid_index_base',0, ...
        'lambda_hat',[]), size(data.xobs,2), 1);
    for eq = 1:numel(equations)
        [~, selected] = min(loss{eq}(1,:));
        assert(loss{eq}(2,selected) == grid(selected), 'Unexpected loss grid');
        values = coef(permutation,eq);
        equations(eq).coefficients_original_scale = values';
        equations(eq).support_indices = (find(values ~= 0)-1)';
        equations(eq).lambda_grid_index = selected-1;
        equations(eq).lambda_hat = grid(selected);
    end
    assert(all(isfinite(coef(:))), 'Nonfinite reference coefficients');
    encoded = jsonencode(result);
    eq_json = cell(1,numel(equations));
    for eq = 1:numel(equations)
        entry = equations(eq);
        numbers = arrayfun(@(v) sprintf('%.17g',v), ...
            entry.coefficients_original_scale, 'UniformOutput',false);
        eq_json{eq} = sprintf(['{"coefficients_original_scale":[%s],' ...
            '"support_indices":[%s],"lambda_grid_index":%d,' ...
            '"lambda_grid_index_base":0,"lambda_hat":%.17g}'], ...
            strjoin(numbers,','), strjoin(arrayfun(@(v) sprintf('%d',v), ...
                entry.support_indices, 'UniformOutput',false),','), ...
            entry.lambda_grid_index, entry.lambda_hat);
    end
    encoded = [encoded(1:end-1) ',"equations":[' strjoin(eq_json,',') ']}'];
    temp = [target '.tmp'];
    fid = fopen(temp, 'w');
    assert(fid >= 0, 'Cannot open output');
    cleanup = onCleanup(@() fclose(fid));
    fprintf(fid, '%s\n', encoded);
    clear cleanup;
    movefile(temp, target);
    fprintf('completed %s\n', cell_info.cell_id);
end
end
